"use client"

import { Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { signIn } from "next-auth/react"
import {
  Container,
  Paper,
  Title,
  Text,
  Button,
  Stack,
  ThemeIcon,
} from "@mantine/core"
import { IconBrandGithub } from "@tabler/icons-react"

function LoginForm() {
  const searchParams = useSearchParams()
  const callbackUrl = searchParams.get("callbackUrl") ?? "/"

  return (
    <Container size={420} my={80}>
      <Paper radius="md" p="xl" withBorder>
        <Stack align="center" gap="lg">
          <Title order={2}>Argus</Title>
          <Text c="dimmed" size="sm" ta="center">
            Sign in to access your agent reliability dashboard.
          </Text>

          <Button
            fullWidth
            size="md"
            leftSection={
              <ThemeIcon variant="transparent" color="white" size="sm">
                <IconBrandGithub size={20} />
              </ThemeIcon>
            }
            onClick={() => signIn("github", { callbackUrl })}
          >
            Sign in with GitHub
          </Button>
        </Stack>
      </Paper>
    </Container>
  )
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  )
}
