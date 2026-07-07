"use client";
import { IconSearch } from "@tabler/icons-react";

export function TopNav({ title }: { title?: string }) {
  return (
    <nav className="topnav">
      {/* Search */}
      <div className="topnav-search">
        <div className="topnav-search-inner">
          <input
            type="search"
            placeholder="Search traces, agents…"
            className="topnav-search-input"
          />
          <button type="button" className="topnav-search-btn" aria-label="Search">
            <IconSearch size={16} />
          </button>
        </div>
      </div>

      {/* Right side */}
      <div className="topnav-right">
        <span
          style={{
            fontSize: 12,
            fontFamily: "var(--lato)",
            background: "var(--light-blue)",
            color: "var(--blue)",
            padding: "4px 12px",
            borderRadius: 20,
            fontWeight: 600,
          }}
        >
          Argus · Alpha
        </span>
      </div>
    </nav>
  );
}
