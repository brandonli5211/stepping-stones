// Reusable component: renders a list of turns. Pages pass data in through props.
export default function Transcript({ turns }) {
  return (
    <ol className="transcript">
      {turns.map((turn) => (
        <li key={turn.turn_number} className={`turn turn-${turn.speaker}`}>
          <span className="speaker">{turn.speaker}</span>
          <span className="text">{turn.text}</span>
          {turn.dialog_acts.length > 0 && (
            <span className="acts">{turn.dialog_acts.join(', ')}</span>
          )}
        </li>
      ))}
    </ol>
  );
}
