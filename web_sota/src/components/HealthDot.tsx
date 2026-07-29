export function HealthDot({ connected }: { connected: boolean | null }) {
  const color =
    connected === null ? "bg-gray-500" : connected ? "bg-green-500" : "bg-red-500";
  return (
    <div className={`w-2 h-2 rounded-full ${color} animate-pulse`} data-testid="backend-dot" />
  );
}
