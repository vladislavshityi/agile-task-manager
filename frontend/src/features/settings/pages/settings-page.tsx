import { PageHeader } from '@/components/page-header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { InvitesSection } from '@/features/invites/components/invites-section'
import { MembersTable } from '@/features/members/components/members-table'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import { ProfileTab } from '../components/profile-tab'
import { WorkspaceTab } from '../components/workspace-tab'

export default function SettingsPage() {
  const { can } = useWorkspace()
  return (
    <div className="mx-auto grid max-w-3xl gap-6">
      <PageHeader title="Настройки" />
      <Tabs defaultValue="profile" className="gap-5">
        <TabsList>
          <TabsTrigger value="profile">Профиль</TabsTrigger>
          <TabsTrigger value="workspace">Пространство</TabsTrigger>
          <TabsTrigger value="members">Участники</TabsTrigger>
        </TabsList>
        <TabsContent value="profile">
          <ProfileTab />
        </TabsContent>
        <TabsContent value="workspace">
          <WorkspaceTab />
        </TabsContent>
        <TabsContent value="members" className="grid gap-8">
          <MembersTable />
          {can('admin') && <InvitesSection />}
        </TabsContent>
      </Tabs>
    </div>
  )
}
