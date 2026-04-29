export default function Nebula({ isSpeaking }) {
  return (
    <div className={`nebula-wrap ${isSpeaking ? 'nebula-active' : ''}`}>
      <div className="nebula-core" />
      <div className="nebula-ring1" />
      <div className="nebula-ring2" />
    </div>
  );
}
