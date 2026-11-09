"use client";

import { useEffect, useState } from "react";
import { ArrowUpIcon, FolderOpenIcon, FolderPlusIcon } from "lucide-animated";

import { Button } from "@/components/ui/button";
import { LoadingIcon } from "@/components/ui/loading-icon";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import { useI18n } from "@/components/i18n-provider";
import { errorMessage } from "@/lib/errors";
import { rootLabel } from "@/lib/labels";
import type { DirectoryListing, RootEntry } from "@/types/api";

interface FolderDialogProps {
  open: boolean;
  initialPath: string;
  roots: RootEntry[];
  onOpenChange: (open: boolean) => void;
  onSelect: (path: string) => void;
}

function rootForPath(path: string, roots: RootEntry[]): string {
  const match = roots.find(
    (root) =>
      path === root.path ||
      path.startsWith(`${root.path}/`) ||
      path.startsWith(`${root.path}\\`),
  );
  return match?.path ?? roots[0]?.path ?? "";
}

export function FolderDialog({
  open,
  initialPath,
  roots,
  onOpenChange,
  onSelect,
}: FolderDialogProps) {
  const { locale, t } = useI18n();
  const [listing, setListing] = useState<DirectoryListing | null>(null);
  const [selectedRoot, setSelectedRoot] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [creatingBusy, setCreatingBusy] = useState(false);

  const load = async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const next = await api.listDirectory(path);
      setListing(next);
      setSelectedRoot(rootForPath(next.path, roots));
    } catch (caught) {
      setError(errorMessage(caught, locale));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!open) {
      return;
    }
    setCreating(false);
    setNewName("");
    const start = initialPath || roots[0]?.path;
    if (start) {
      void load(start);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, initialPath, roots]);

  const createFolder = async () => {
    if (!listing || !newName.trim() || creatingBusy) {
      return;
    }
    setCreatingBusy(true);
    setError(null);
    try {
      await api.createDirectory(listing.path, newName);
      setNewName("");
      setCreating(false);
      await load(listing.path);
    } catch (caught) {
      setError(errorMessage(caught, locale));
    } finally {
      setCreatingBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md gap-0 p-0">
        <DialogHeader className="px-5 pb-3 pt-5">
          <DialogTitle>{t("folder.title")}</DialogTitle>
        </DialogHeader>

        <div className="space-y-3 px-5 pb-4">
          {roots.length > 1 ? (
            <Select
              value={selectedRoot}
              onValueChange={(path) => {
                void load(path);
              }}
            >
              <SelectTrigger aria-label={t("folder.location")}>
                <SelectValue placeholder={t("folder.location")} />
              </SelectTrigger>
              <SelectContent>
                {roots.map((root) => (
                  <SelectItem key={root.path} value={root.path}>
                    {rootLabel(root.label, t)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : null}

          <div className="flex items-center gap-2 rounded-lg border px-3 py-2">
            <FolderOpenIcon
              size={16}
              className="shrink-0 text-muted-foreground"
            />
            <span
              className="truncate text-xs text-muted-foreground"
              title={listing?.path ?? initialPath}
            >
              {listing?.path ?? initialPath}
            </span>
          </div>

          <div className="h-64 overflow-y-auto rounded-lg border">
            {loading ? (
              <div className="flex h-full items-center justify-center">
                <LoadingIcon size={16} className="text-muted-foreground" />
              </div>
            ) : (
              <div className="p-1">
                {listing?.parent ? (
                  <button
                    type="button"
                    onClick={() => {
                      void load(listing.parent as string);
                    }}
                    className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                  >
                    <ArrowUpIcon size={16} />
                    <span>{t("folder.parent")}</span>
                  </button>
                ) : null}

                {listing?.directories.map((directory) => (
                  <button
                    key={directory.path}
                    type="button"
                    onClick={() => {
                      void load(directory.path);
                    }}
                    className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors hover:bg-accent"
                  >
                    <FolderOpenIcon
                      size={16}
                      className="shrink-0 text-muted-foreground"
                    />
                    <span className="truncate">{directory.name}</span>
                  </button>
                ))}

                {!listing?.parent && listing?.directories.length === 0 ? (
                  <p className="px-2.5 py-6 text-center text-xs text-muted-foreground">
                    {t("folder.empty")}
                  </p>
                ) : null}
              </div>
            )}
          </div>

          {creating ? (
            <form
              className="flex gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                void createFolder();
              }}
            >
              <input
                value={newName}
                onChange={(event) => setNewName(event.target.value)}
                placeholder={t("folder.namePlaceholder")}
                autoFocus
                maxLength={120}
                className="h-9 min-w-0 flex-1 rounded-lg border border-border bg-transparent px-3 text-sm outline-none focus:ring-2 focus:ring-ring/40"
              />
              <Button
                type="submit"
                size="sm"
                disabled={!newName.trim() || creatingBusy}
              >
                {creatingBusy ? <LoadingIcon size={16} /> : t("folder.create")}
              </Button>
            </form>
          ) : null}

          {error ? (
            <p className="text-xs text-destructive" role="alert">
              {error}
            </p>
          ) : null}
        </div>

        <DialogFooter className="border-t px-5 py-3 sm:justify-between">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setCreating((value) => !value)}
          >
            <FolderPlusIcon size={16} />
            {t("folder.new")}
          </Button>
          <div className="flex gap-2">
            <DialogClose asChild>
              <Button type="button" variant="ghost" size="sm">
                {t("common.cancel")}
              </Button>
            </DialogClose>
            <Button
              type="button"
              size="sm"
              disabled={!listing || loading}
              onClick={() => {
                if (listing) {
                  onSelect(listing.path);
                  onOpenChange(false);
                }
              }}
            >
              {t("folder.select")}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
