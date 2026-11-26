// 삭제 확인, 첫 수집 대기 중 자동 새로고침, 서비스 워커 등록
document.querySelectorAll("form[data-confirm]").forEach(function (f) {
  f.addEventListener("submit", function (e) {
    if (!window.confirm(f.dataset.confirm)) e.preventDefault();
  });
});
if (document.querySelector("[data-pending]")) {
  var tries = Number(sessionStorage.getItem("pendingTries") || 0);
  if (tries < 10) {
    sessionStorage.setItem("pendingTries", tries + 1);
    setTimeout(function () { location.replace(location.pathname); }, 2500);
  }
} else {
  try { sessionStorage.removeItem("pendingTries"); } catch (e) { /* 저장소를 못 쓰는 환경 */ }
}
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");
