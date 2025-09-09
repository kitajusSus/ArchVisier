#include "PdfPreviewWidget.h"

#include <QPdfView>
#include <QVBoxLayout>

PdfPreviewWidget::PdfPreviewWidget(QWidget *parent)
    : QWidget(parent), m_view(new QPdfView(this))
{
    m_view->setDocument(&m_doc);
    auto layout = new QVBoxLayout(this);
    layout->addWidget(m_view);
}

bool PdfPreviewWidget::loadPdf(const QString &filePath)
{
    auto err = m_doc.load(filePath);
    m_view->setPageMode(QPdfView::SinglePage);
    return err == QPdfDocument::NoError;
}
