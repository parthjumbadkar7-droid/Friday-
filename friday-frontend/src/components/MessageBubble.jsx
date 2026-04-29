import { Star } from 'lucide-react';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isProactive = message.proactive === true;

  return (
    <div className={`msg-row ${isUser ? 'msg-row-user' : 'msg-row-friday'}`}>
      <div className={`msg-bubble ${isUser ? 'msg-bubble-user' : 'msg-bubble-friday'}`}>
        {isProactive && (
          <span className="msg-proactive-badge">
            <Star size={10} className="inline mr-1" />
            FRIDAY
          </span>
        )}
        <p className="msg-text">{message.content}</p>
        {message.timestamp && (
          <span className="msg-time">
            {new Date(message.timestamp).toLocaleTimeString('en-IN', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        )}
      </div>
    </div>
  );
}
