import { useState } from "react";
import { ExternalLink, Share2, Instagram, Twitter, Linkedin, Youtube } from "lucide-react";

const ICONS: Record<string, any> = { instagram: Instagram, twitter: Twitter, linkedin: Linkedin, youtube: Youtube };

export function ShareButtons({ url, title }: { url: string; title: string }) {
  const encoded = encodeURIComponent(url);
  return (
    <div className="flex items-center gap-2">
      <Share2 size={14} className="text-zinc-500" />
      {[
        { name: "Twitter", href: `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encoded}` },
        { name: "Facebook", href: `https://www.facebook.com/sharer/sharer.php?u=${encoded}` },
        { name: "LinkedIn", href: `https://www.linkedin.com/sharing/share-offsite/?url=${encoded}` },
        { name: "Email", href: `mailto:?subject=${encodeURIComponent(title)}&body=${encoded}` },
      ].map((s) => (
        <a key={s.name} href={s.href} target="_blank" rel="noreferrer"
          className="text-xs px-2 py-1 bg-zinc-800 text-zinc-400 rounded hover:text-zinc-200 hover:bg-zinc-700 transition-colors">
          {s.name}
        </a>
      ))}
    </div>
  );
}

export function SocialPage() {
  const links = [
    { platform: "instagram", url: "", label: "Instagram" },
    { platform: "twitter", url: "", label: "Twitter" },
    { platform: "facebook", url: "", label: "Facebook" },
    { platform: "linkedin", url: "", label: "LinkedIn" },
    { platform: "youtube", url: "", label: "YouTube" },
  ];

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-zinc-100 mb-6">Follow Us</h1>
      <div className="grid grid-cols-2 gap-3">
        {links.map((l) => {
          const Icon = ICONS[l.platform] || ExternalLink;
          return (
            <a key={l.platform} href={l.url || "#"} target={l.url ? "_blank" : undefined} rel="noreferrer"
              className="flex items-center gap-3 bg-zinc-900 border border-zinc-800 rounded-lg p-4 hover:border-zinc-700 transition-colors">
              <Icon size={20} className="text-amber-500" />
              <span className="text-sm text-zinc-200">{l.label}</span>
              {l.url && <ExternalLink size={12} className="ml-auto text-zinc-600" />}
            </a>
          );
        })}
      </div>
    </div>
  );
}
