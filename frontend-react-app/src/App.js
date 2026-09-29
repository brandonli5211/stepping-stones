import { useEffect, useState } from 'react';

const CONVERSATION_URL = 'http://localhost:8080/api/conversation/1';

function App() {
  const [conversation, setConversation] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();

    fetch(CONVERSATION_URL, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Request failed: ${response.status}`);
        }
        return response.json();
      })
      .then(setConversation)
      .catch((fetchError) => {
        if (fetchError.name !== 'AbortError') {
          setError(fetchError.message);
        }
      });

    return () => controller.abort();
  }, []);

  if (error) {
    return <main><p role="alert">Could not load the conversation: {error}</p></main>;
  }

  if (!conversation) {
    return <main><p>Loading conversation...</p></main>;
  }

  return (
    <main>
      <h1>Conversation {conversation.conversationId || conversation.id}</h1>
      <ol>
        {conversation.transcript.map((entry, index) => (
          <li key={`${index}-${entry.speaker}`}>
            <strong>{entry.speaker}:</strong> {entry.text}
          </li>
        ))}
      </ol>
    </main>
  );
}

export default App;