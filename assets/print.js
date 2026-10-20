// 「인쇄 / PDF로 저장」 버튼: 브라우저 인쇄 창에서 「PDF로 저장」을 고르면 된다 (print.css 가 글만 남김)
document.addEventListener('click', function (e) { var b = e.target.closest && e.target.closest('[data-print]'); if (!b) return; e.preventDefault(); try { window.gtag && gtag('event', 'print_pdf', { p: location.pathname }); } catch (x) {} window.print(); });
document.addEventListener('click', function (e) { var a = e.target.closest && e.target.closest('a[data-pdf]'); if (a) try { window.gtag && gtag('event', 'pdf_download', { p: location.pathname }); } catch (x) {} });
