#pragma once

#include <QMainWindow>

class PdfPreviewWidget;
class PythonClient;

class MainWindow : public QMainWindow
{
    Q_OBJECT
public:
    explicit MainWindow(QWidget *parent = nullptr);

private slots:
    void onPingResponse(const QString &text);
    void sendPing();

private:
    PdfPreviewWidget *m_preview;
    PythonClient *m_client;
};
