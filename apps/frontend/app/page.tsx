import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <h1>Semantic Reasoning Agent</h1>
      <p>Production web scaffold for Phase A validation.</p>
      <ul>
        <li>
          <Link href="/ontology">Ontology workspace</Link>
        </li>
        <li>
          <Link href="/ontology/builds">Ontology builds</Link>
        </li>
        <li>
          <Link href="/ontology/review">Ontology review queue</Link>
        </li>
      </ul>
    </main>
  );
}
