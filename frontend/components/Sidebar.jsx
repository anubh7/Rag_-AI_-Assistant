import React from "react";

export default function Sidebar({ collections, activeCollection, onSelect }) {
  return (
    <aside className="sidebar">
      <h3>Collections</h3>
      <ul>
        {collections.map((name) => (
          <li
            key={name}
            className={name === activeCollection ? "active" : ""}
            onClick={() => onSelect(name)}
          >
            {name}
          </li>
        ))}
      </ul>
    </aside>
  );
}
