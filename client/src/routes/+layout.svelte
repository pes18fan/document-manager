<script lang="ts">
    import "./layout.css";
    import favicon from "$lib/assets/favicon.svg";

    import { ModeWatcher } from "mode-watcher";

    import MoonIcon from "@lucide/svelte/icons/moon";
    import SunIcon from "@lucide/svelte/icons/sun";
    import HomeIcon from "@lucide/svelte/icons/home";
    import UploadIcon from "@lucide/svelte/icons/upload";
    import FileTextIcon from "@lucide/svelte/icons/file-text";

    import { toggleMode } from "mode-watcher";
    import { Button } from "$lib/components/ui/button";
    import * as NavigationMenu from "$lib/components/ui/navigation-menu";

    let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
<ModeWatcher />

<div class="min-h-screen flex flex-col">
    <!-- Navigation Bar -->
    <nav
        class="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50"
    >
        <div class="container mx-auto px-6 py-3">
            <div class="flex items-center justify-between">
                <!-- Logo/Brand -->
                <a
                    href="/"
                    class="flex items-center gap-2 hover:opacity-80 transition-opacity no-underline text-accent-foreground"
                >
                    <FileTextIcon class="h-6 w-6" />
                    <span class="text-xl font-bold">Document Manager</span>
                </a>

                <!-- Navigation Links -->
                <div class="flex items-center gap-4">
                    <NavigationMenu.Root>
                        <NavigationMenu.List>
                            <NavigationMenu.Item>
                                <NavigationMenu.Link
                                    href="/upload"
                                    class="flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground rounded-md no-underline text-muted-foreground"
                                >
                                    <UploadIcon class="h-4 w-4" />
                                    <span>Upload</span>
                                </NavigationMenu.Link>
                            </NavigationMenu.Item>
                        </NavigationMenu.List>
                    </NavigationMenu.Root>

                    <!-- Theme Toggle -->
                    <div class="ml-2 pl-4 border-l border-border">
                        <Button
                            onclick={toggleMode}
                            variant="outline"
                            size="icon"
                        >
                            <SunIcon
                                class="h-[1.2rem] w-[1.2rem] scale-100 rotate-0 !transition-all dark:scale-0 dark:-rotate-90"
                            />
                            <MoonIcon
                                class="absolute h-[1.2rem] w-[1.2rem] scale-0 rotate-90 !transition-all dark:scale-100 dark:rotate-0"
                            />
                            <span class="sr-only">Toggle theme</span>
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-1">
        {@render children()}
    </main>
</div>
