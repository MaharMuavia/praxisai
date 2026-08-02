export function MoneyAmount({
  amountMinor,
  currency,
}: {
  amountMinor: number;
  currency: string;
}) {
  return (
    <span>
      {new Intl.NumberFormat("en", { style: "currency", currency }).format(
        amountMinor / 100,
      )}
    </span>
  );
}
