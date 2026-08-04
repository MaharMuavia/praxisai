import { InternshipProgramPage } from "@/features/internships/internship-public";

export default async function InternshipProgramRoute({
  params,
}: {
  params: Promise<{ programSlug: string }>;
}) {
  const { programSlug } = await params;
  return <InternshipProgramPage slug={programSlug} />;
}
