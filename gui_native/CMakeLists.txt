cmake_minimum_required(VERSION 3.16)
project(gui_native LANGUAGES CXX)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 COMPONENTS Widgets Network PdfWidgets QUIET)
if(Qt6_FOUND)
    set(QT_LIBS Qt6::Widgets Qt6::Network Qt6::PdfWidgets)
else()
    find_package(Qt5 COMPONENTS Widgets Network REQUIRED)
    set(QT_LIBS Qt5::Widgets Qt5::Network)
endif()

set(SOURCES
    main.cpp
    MainWindow.cpp
    PdfPreviewWidget.cpp
    PythonClient.cpp
)

add_executable(gui_native WIN32 ${SOURCES})

target_link_libraries(gui_native PRIVATE ${QT_LIBS})
