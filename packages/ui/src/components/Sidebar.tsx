"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { NavLink, Text } from "@mantine/core";
import {
  IconLayoutDashboard,
  IconTimeline,
  IconCoins,
  IconChartBar,
  IconEye,
} from "@tabler/icons-react";

const NAV_ITEMS = [
  { href: "/",        label: "Dashboard", icon: IconLayoutDashboard },
  { href: "/traces",  label: "Traces",    icon: IconTimeline },
  { href: "/finops",  label: "FinOps",    icon: IconCoins },
  { href: "/evals",   label: "Evals",     icon: IconChartBar },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <Link href="/" className="sidebar-logo">
        <IconEye size={20} color="#2563eb" stroke={1.8} />
        <span className="sidebar-logo-text">Argus</span>
      </Link>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <NavLink
              key={href}
              component={Link}
              href={href}
              label={label}
              leftSection={<Icon size={16} stroke={1.8} />}
              active={active}
              styles={{
                root: {
                  borderRadius: "6px",
                  fontSize: "13px",
                  fontWeight: 500,
                  marginBottom: "2px",
                  paddingTop: "8px",
                  paddingBottom: "8px",
                  ...(active && {
                    borderLeft: "2px solid #2563eb",
                    paddingLeft: "10px",
                    background: "#eff6ff",
                    color: "#1d4ed8",
                  }),
                },
              }}
            />
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <Text size="xs" c="dimmed">Argus by Perciqa</Text>
      </div>
    </aside>
  );
}
