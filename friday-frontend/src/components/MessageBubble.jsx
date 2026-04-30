import { useState } from 'react';
import { Star, Pencil, Check, X } from 'lucide-react';

export default function MessageBubble({ message, onEdit }) {
  const isUser = message.role === 'user';
  const isProactive = message.proactive === true;
  
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.content);

  const handleSave = () => {
    if (onEdit && editText.trim() !== message.content) {
      onEdit(message.id || message.timestamp, editText);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditText(message.content);
    setIsEditing(false);
  };

  return (
    <div className={`msg-row ${isUser ? 'msg-row-user' : 'msg-row-friday'} group`}>
      <div className={`msg-bubble ${isUser ? 'msg-bubble-user' : 'msg-bubble-friday'}`}>
        {isProactive && (
          <span className="msg-proactive-badge">
            <Star size={10} className="inline mr-1" />
            FRIDAY
          </span>
        )}
        
        {isEditing ? (
          <div className="flex flex-col gap-2 w-full">
            <textarea 
              className="bg-transparent border border-purple-500/50 rounded p-2 text-white text-sm outline-none resize-none"
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              rows={3}
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <button onClick={handleCancel} className="text-gray-400 hover:text-white transition-colors">
                <X size={14} />
              </button>
              <button onClick={handleSave} className="text-purple-400 hover:text-purple-300 transition-colors">
                <Check size={14} />
              </button>
            </div>
          </div>
        ) : (
          <div className="relative">
            <p className="msg-text whitespace-pre-wrap">{message.content}</p>
            {!isUser && (
              <button 
                onClick={() => setIsEditing(true)}
                className="absolute -right-8 top-0 opacity-0 group-hover:opacity-100 text-gray-500 hover:text-purple-400 transition-all"
                title="Edit response"
              >
                <Pencil size={12} />
              </button>
            )}
          </div>
        )}

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
