// 삭제 확인과 서비스 워커 등록
document.querySelectorAll("form[data-confirm]").forEach(function (f) {
  f.addEventListener("submit", function (e) {
    if (!window.confirm(f.dataset.confirm)) e.preventDefault();
  });
});
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");
