#pragma once

#include <QPdfDocument>
#include <QWidget>

class QPdfView;

class PdfPreviewWidget : public QWidget
{
    Q_OBJECT
public:
    explicit PdfPreviewWidget(QWidget *parent = nullptr);
    bool loadPdf(const QString &filePath);

private:
    QPdfDocument m_doc;
    QPdfView *m_view;
};
