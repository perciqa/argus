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
      { href: "/",        label: "Overview",  icon: IconLayoutDashboard },
      { href: "/traces",  label: "Traces",    icon: IconTimeline },
    ],
  },
  {
    section: "Analyze",
    items: [
      { href: "/finops",  label: "FinOps",    icon: IconCoins },
      { href: "/evals",   label: "Evals",     icon: IconChartBar },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  function isActive(href: string) {
    return href === "/" ? pathname === "/" : pathname.startsWith(href);
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <Link href="/" className="sidebar-logo">
        <div className="sidebar-logo-mark">
          <IconEye size={16} color="white" stroke={2} />
        </div>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-name">Argus</span>
          <span className="sidebar-logo-sub">by Perciqa</span>
        </div>
      </Link>

      {/* Nav */}
      <nav className="sidebar-nav">
        {NAV.map(({ section, items }) => (
          <div key={section}>
            <span className="sidebar-section-label">{section}</span>
            {items.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={`sidebar-nav-item ${isActive(href) ? "active" : ""}`}
              >
                <Icon size={15} stroke={1.8} className="nav-icon" />
                {label}
              </Link>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-footer-version">
          <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <IconActivity size={11} />
            v0.1.0-alpha
          </span>
          <span>MIT</span>
        </div>
      </div>
    </aside>
  );
}
