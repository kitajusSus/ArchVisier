#include "PythonClient.h"

#include <QNetworkReply>
#include <QNetworkRequest>
#include <QUrl>

PythonClient::PythonClient(QObject *parent) : QObject(parent)
{
    connect(&m_manager, &QNetworkAccessManager::finished,
            this, &PythonClient::handleReply);
}

void PythonClient::ping()
{
    QNetworkRequest req(QUrl("http://127.0.0.1:5000/ping"));
    m_manager.get(req);
}

void PythonClient::handleReply(QNetworkReply *reply)
{
    const QString payload = reply->readAll();
    emit responseReceived(payload);
    reply->deleteLater();
}
