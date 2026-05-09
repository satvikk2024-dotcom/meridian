import {
  TrendingUp,
  BookOpen,
  MessageSquare,
  GitFork,
  Newspaper,
  Globe,
} from "lucide-react";

export type SourceType = "yfinance" | "bse" | "wikipedia" | "reddit" | "github" | "news" | string;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const ICON_MAP: Record<string, React.ComponentType<any>> = {
  yfinance:  TrendingUp,
  bse:       TrendingUp,
  wikipedia: BookOpen,
  reddit:    MessageSquare,
  github:    GitFork,
  news:      Newspaper,
};

interface SourceIconProps {
  source: SourceType;
  size?: number;
  className?: string;
}

export default function SourceIcon({ source, size = 14, className = "" }: SourceIconProps) {
  const Icon = ICON_MAP[source.toLowerCase()] ?? Globe;
  return <Icon size={size} className={className} />;
}
