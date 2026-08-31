export function ConfirmationCard({message, onConfirm}: {message: string; onConfirm: () => void}) {
  return <div role="alert"><p>{message}</p><button onClick={onConfirm}>确认</button></div>;
}
