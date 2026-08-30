// 브라우저 안에서 벌어지는 움직임을 담당하는 파일
// 서버는 이 파일 내용을 모른다. 브라우저가 받아서 자기 안에서 실행한다

// 브라우저의 오늘 날짜를 "2026-08-30" 모양으로 만들어서
// index.html 의 <span id="today"> 안에 써넣는다
const today = new Date();
const text = today.getFullYear() + "-"
    + String(today.getMonth() + 1).padStart(2, "0") + "-"   // 월은 0부터 세서 +1
    + String(today.getDate()).padStart(2, "0");

document.getElementById("today").textContent = text;

console.log("main.js 로딩됨, 오늘은", text);
