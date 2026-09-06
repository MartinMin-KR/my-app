// 브라우저 안에서 벌어지는 움직임을 담당하는 파일
// 서버는 이 파일 내용을 모른다. 브라우저가 받아서 자기 안에서 실행한다

// 브라우저의 오늘 날짜를 "2026-08-30" 모양으로 만들어서
// index.html 의 <span id="today"> 안에 써넣는다
const today = new Date();
const text = today.getFullYear() + "-"
    + String(today.getMonth() + 1).padStart(2, "0") + "-"   // 월은 0부터 세서 +1
    + String(today.getDate()).padStart(2, "0");

document.getElementById("today").textContent = text;

// ── 삭제 버튼 ──────────────────────────────────────────────
// 화면의 모든 삭제 버튼을 찾아서, 각각에 "클릭되면 할 일"을 예약해 둔다
document.querySelectorAll(".delete-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
        // 버튼에 메모된 번호와 이름을 읽는다 (index.html 의 data-id, data-name)
        const id = btn.dataset.id;
        const name = btn.dataset.name;

        // 확인창. [취소]를 누르면 여기서 끝 — 아무것도 안 보낸다
        if (!confirm("정말 " + name + "를 삭제할까요?")) {
            return;
        }

        // 브라우저에게 "이 주소로, DELETE 방식으로 쪽지 보내줘"라고 접수
        fetch("/expenses/" + id, { method: "DELETE" })
            .then(function (response) {
                // 답장이 도착하면 실행되는 부분
                if (response.ok) {
                    // 화면과 DB 를 일치시키기 위해 통째로 새로고침 (합계도 같이 갱신됨)
                    location.reload();
                } else {
                    alert("삭제에 실패했어요 (" + response.status + ")");
                }
            });
    });
});

console.log("main.js 로딩됨, 오늘은", text);
