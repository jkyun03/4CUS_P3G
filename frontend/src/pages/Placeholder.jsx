// 아직 만들지 않은 화면용 임시 페이지
export default function Placeholder({ title }) {
  return (
    <div>
      <h1 className="page-title">{title}</h1>
      <div className="empty">이 화면은 준비 중입니다. 와이어프레임 기준으로 이어서 구현할 수 있어요.</div>
    </div>
  );
}
