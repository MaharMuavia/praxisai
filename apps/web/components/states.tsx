export function EmptyState({
  title,
  detail,
}: {
  title: string;
  detail: string;
}) {
  return (
    <div className="empty">
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}

export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div className="error" role="alert">
      <p>{message}</p>
      {retry && (
        <button className="button button-ghost" onClick={retry}>
          Retry
        </button>
      )}
    </div>
  );
}
