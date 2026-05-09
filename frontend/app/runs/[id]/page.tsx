import RunPageClient from "./RunPageClient";

interface Props {
  params: { id: string };
  searchParams: { company?: string; ticker?: string };
}

export default function RunPage({ params, searchParams }: Props) {
  const company = searchParams.company ?? params.id;
  const ticker  = searchParams.ticker  ?? "";
  return <RunPageClient company={company} ticker={ticker} />;
}
