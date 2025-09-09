#ifdef _WIN32
#define _CRT_SECURE_NO_WARNINGS // suppress MSVC warnings for standard C
                                // functions
#endif

#include <algorithm>
#include <atomic>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <mutex>
#include <random>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

#include "tesseract/baseapi.h"
#include "tesseract/include/leptonica/allheaders.h"

namespace fs = std::filesystem;

std::string get_env(const char *name, const std::string &def = "") {
#ifdef _WIN32
  // Use secure _dupenv_s on Windows to avoid deprecated getenv
  char *buffer = nullptr;
  size_t len = 0;
  if (_dupenv_s(&buffer, &len, name) == 0 && buffer) {
    std::string val(buffer);
    free(buffer);
    return val;
  }
  return def;
#else
  // POSIX provides thread-safe getenv
  const char *val = std::getenv(name);
  return val ? std::string(val) : def;
#endif
}

std::string random_uuid() {
  std::random_device rd;
  std::uniform_int_distribution<int> dist(0, 15);
  std::stringstream ss;
  for (int i = 0; i < 32; ++i) {
    ss << std::hex << dist(rd);
  }
  return ss.str();
}

struct TempDir {
  fs::path path;
  TempDir() : path(fs::temp_directory_path() / random_uuid()) {
    fs::create_directories(path);
  }
  ~TempDir() {
    std::error_code ec;
    fs::remove_all(path, ec);
  }
};

struct CommandResult {
  bool ok;
  std::string output;
  std::string error;
};

CommandResult run_command(const std::vector<std::string> &args,
                          bool capture = true) {
  CommandResult res{true, "", ""};
  if (args.empty()) {
    res.ok = false;
    res.error = "Empty command";
    return res;
  }
#ifdef _WIN32
  std::string cmdline;
  for (const auto &arg : args) {
    if (!cmdline.empty())
      cmdline += ' ';
    cmdline += '"';
    for (char c : arg) {
      if (c == '"')
        cmdline += '\\';
      cmdline += c;
    }
    cmdline += '"';
  }

  SECURITY_ATTRIBUTES sa{sizeof(SECURITY_ATTRIBUTES), nullptr, TRUE};
  HANDLE read_pipe = nullptr, write_pipe = nullptr;
  if (capture) {
    if (!CreatePipe(&read_pipe, &write_pipe, &sa, 0)) {
      res.ok = false;
      res.error = "CreatePipe failed";
      return res;
    }
    SetHandleInformation(read_pipe, HANDLE_FLAG_INHERIT, 0);
  }

  STARTUPINFOA si{};
  si.cb = sizeof(si);
  if (capture) {
    si.hStdOutput = si.hStdError = write_pipe;
    si.dwFlags |= STARTF_USESTDHANDLES;
  }

  PROCESS_INFORMATION pi{};
  if (!CreateProcessA(nullptr, cmdline.data(), nullptr, nullptr, capture, 0,
                      nullptr, nullptr, &si, &pi)) {
    if (capture) {
      CloseHandle(read_pipe);
      CloseHandle(write_pipe);
    }
    res.ok = false;
    res.error = "CreateProcess failed";
    return res;
  }

  CloseHandle(pi.hThread);
  if (capture)
    CloseHandle(write_pipe);

  std::string output;
  if (capture) {
    char buffer[256];
    DWORD read;
    while (ReadFile(read_pipe, buffer, sizeof(buffer), &read, nullptr) &&
           read > 0) {
      res.output.append(buffer, read);
    }
    CloseHandle(read_pipe);
  }

  WaitForSingleObject(pi.hProcess, INFINITE);
  DWORD exit_code = 0;
  GetExitCodeProcess(pi.hProcess, &exit_code);
  CloseHandle(pi.hProcess);
  if (exit_code != 0) {
    res.ok = false;
    res.error = "Command failed: " + args[0];
  }
  return res;
#else
  int pipefd[2];
  if (capture && pipe(pipefd) == -1) {
    res.ok = false;
    res.error = "pipe failed";
    return res;
  }

  pid_t pid = fork();
  if (pid == -1) {
    if (capture) {
      close(pipefd[0]);
      close(pipefd[1]);
    }
    res.ok = false;
    res.error = "fork failed";
    return res;
  }

  if (pid == 0) {
    if (capture) {
      close(pipefd[0]);
      dup2(pipefd[1], STDOUT_FILENO);
      dup2(pipefd[1], STDERR_FILENO);
      close(pipefd[1]);
    }
    std::vector<char *> cargs;
    for (const auto &arg : args)
      cargs.push_back(const_cast<char *>(arg.c_str()));
    cargs.push_back(nullptr);
    execvp(cargs[0], cargs.data());
    _exit(127);
  }

  if (capture) {
    close(pipefd[1]);
    char buffer[256];
    ssize_t n;
    while ((n = read(pipefd[0], buffer, sizeof(buffer))) > 0) {
      res.output.append(buffer, n);
    }
    close(pipefd[0]);
    int status = 0;
    waitpid(pid, &status, 0);
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
      res.ok = false;
      res.error = "Command failed: " + args[0];
    }
    return res;
  } else {
    int status = 0;
    waitpid(pid, &status, 0);
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
      res.ok = false;
      res.error = "Command failed: " + args[0];
    }
    return res;
  }
#endif
}

std::string escape_json(const std::string &in) {
  std::string out;
  for (char c : in) {
    switch (c) {
    case '\\':
      out += "\\\\";
      break;
    case '"':
      out += "\\\"";
      break;
    case '\n':
      out += "\\n";
      break;
    case '\r':
      out += "\\r";
      break;
    case '\t':
      out += "\\t";
      break;
    default:
      out += c;
      break;
    }
  }
  return out;
}

std::string ocr_pdf(const std::string &pdf_path,
                    const std::string &tessdata_prefix,
                    const std::string &pdftoppm, std::string &error) {
  TempDir tmp;
  std::string prefix = (tmp.path / "page").string();

  // Konwersja PDF -> obrazy
  auto conv =
      run_command({pdftoppm, "-png", "-r", "300", pdf_path, prefix}, false);
  if (!conv.ok) {
    error = conv.error;
    return "";
  }

  tesseract::TessBaseAPI api;
  if (api.Init(tessdata_prefix.empty() ? nullptr : tessdata_prefix.c_str(),
               "pol")) {
    error = "Nie można zainicjować Tesseract";
    return "";
  }

  std::string text;
  for (int i = 1;; ++i) {
    std::string image = prefix + "-" + std::to_string(i) + ".png";
    if (!fs::exists(image))
      break;
    Pix *pix = pixRead(image.c_str());
    if (!pix)
      break;
    api.SetImage(pix);
    char *out = api.GetUTF8Text();
    if (out) {
      text += out;
      delete[] out;
    }
    pixDestroy(&pix);
    fs::remove(image);
  }
  api.End();

  return text;
}

int main(int argc, char *argv[]) {
  if (argc <= 1)
    return 0;

  std::string tessdata_prefix = get_env("TESSDATA_PREFIX");
  std::string poppler_path = get_env("POPPLER_PATH");
  std::string pdftoppm_cmd =
      poppler_path.empty() ? "pdftoppm" : poppler_path + "/pdftoppm";

  std::vector<std::string> paths;
  for (int i = 1; i < argc; ++i)
    paths.emplace_back(argv[i]);

  std::vector<std::string> results(paths.size());
  std::vector<std::thread> workers;
  std::atomic<size_t> next{0};
  std::mutex error_mutex;
  std::vector<std::string> errors;
  size_t max_threads = std::min<size_t>(
      std::max<unsigned>(1, std::thread::hardware_concurrency()), paths.size());

  for (size_t t = 0; t < max_threads; ++t) {
    workers.emplace_back([&, t]() {
      while (true) {
        size_t i = next.fetch_add(1);
        if (i >= paths.size())
          break;
        std::string err;
        std::string res = ocr_pdf(paths[i], tessdata_prefix, pdftoppm_cmd, err);
        if (!err.empty()) {
          std::lock_guard<std::mutex> lock(error_mutex);
          errors.push_back("Failed to process " + paths[i] + ": " + err);
        } else {
          results[i] = std::move(res);
        }
      }
    });
  }

  for (auto &t : workers)
    t.join();

  for (const auto &err : errors) {
    std::cerr << err << std::endl;
  }

  // Output JSON array
  std::cout << "[";
  for (size_t i = 0; i < results.size(); ++i) {
    std::cout << '"' << escape_json(results[i]) << '"';
    if (i + 1 < results.size())
      std::cout << ",";
  }
  std::cout << "]";
  return errors.empty() ? 0 : 1;
}
