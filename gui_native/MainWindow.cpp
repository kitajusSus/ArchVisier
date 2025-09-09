#include "MainWindow.h"
#include "PdfPreviewWidget.h"
#include "PythonClient.h"

#include <QMessageBox>
#include <QPushButton>
#include <QVBoxLayout>
#include <QWidget>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent),
      m_preview(new PdfPreviewWidget(this)),
      m_client(new PythonClient(this))
{
    auto central = new QWidget(this);
    auto layout = new QVBoxLayout(central);
    auto btn = new QPushButton(tr("Ping Python"), this);

    layout->addWidget(m_preview);
    layout->addWidget(btn);
    setCentralWidget(central);

    connect(btn, &QPushButton::clicked, this, &MainWindow::sendPing);
    connect(m_client, &PythonClient::responseReceived,
            this, &MainWindow::onPingResponse);
}

void MainWindow::onPingResponse(const QString &text)
{
    QMessageBox::information(this, tr("Server response"), text);
}

void MainWindow::sendPing()
{
    m_client->ping();
}
