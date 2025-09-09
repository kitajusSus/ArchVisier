#pragma once

#include <QObject>
#include <QNetworkAccessManager>

class PythonClient : public QObject
{
    Q_OBJECT
public:
    explicit PythonClient(QObject *parent = nullptr);
    void ping();

signals:
    void responseReceived(const QString &text);

private slots:
    void handleReply(QNetworkReply *reply);

private:
    QNetworkAccessManager m_manager;
};
