"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  IconLayoutDashboard,
  IconTimeline,
  IconCoins,
  IconChartBar,
  IconEye,
  IconActivity,
} from "@tabler/icons-react";

const NAV = [
  {
    section: "Monitor",
    items: [
      { href: "/",       label: "Overview", icon: IconLayoutDashboard },
      { href: "/traces", label: "Traces",   icon: IconTimeline },
    ],
  },
  {
    section: "Analyze",
    items: [
      { href: "/finops", label: "FinOps", icon: IconCoins },
      { href: "/evals",  label: "Evals",  icon: IconChartBar },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  function isActive(href: string) {
    return href === "/" ? pathname === "/" : pathname.startsWith(href);
  }

  return (
    <section id="sidebar" className="sidebar">
      {/* Brand */}
      <Link href="/" className="sidebar-logo">
        <div className="sidebar-logo-mark">
          <IconEye size={22} color="#3C91E6" stroke={2} />
        </div>
        <div className="sidebar-logo-text-wrap">
          <span className="sidebar-logo-name">Argus</span>
          <span className="sidebar-logo-sub">by Perciqa</span>
        </div>
      </Link>

      {/* Nav */}
      <nav className="sidebar-nav">
        {NAV.map(({ section, items }) => (
          <div key={section}>
            <span className="sidebar-section-label">{section}</span>
            {items.map(({ href, label, icon: Icon }) => {
              const active = isActive(href);
              return (
                <div
                  key={href}
                  className={`sidebar-nav-item-wrap ${active ? "active" : ""}`}
                >
                  <Link href={href} className="sidebar-nav-item">
                    <span className="nav-icon">
                      <Icon size={18} stroke={1.8} />
                    </span>
                    <span className="nav-label">{label}</span>
                  </Link>
                </div>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <IconActivity size={11} />
          v0.1.0-alpha
        </span>
        <span>MIT</span>
      </div>
    </section>
  );
}
