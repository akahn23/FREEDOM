/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * publicフォルダ操作api
 * 生成AI製
 */
import { NextRequest, NextResponse } from "next/server";
import {
  mkdir,
  readdir,
  readFile,
  stat,
  unlink,
  writeFile,
} from "fs/promises";
import path from "path";
import type { GetFolderFilesResponse } from "@/types/api/files";

export const runtime = "nodejs";

const BASE_DIR = path.join(process.cwd(), "uploads");

type RouteParams = {
  params: Promise<{
    folder?: string[];
  }>;
};

/**
 * ベースディレクトリ配下に限定して安全にパスを結合する。
 * `..` やパス区切り文字を含む不正なセグメントを拒否しパストラバーサルを防止する。
 */
function safeJoin(base: string, segments: string[]) {
  if (segments.some((segment) => !isSafePathSegment(segment))) {
    return null;
  }

  const targetPath = path.join(base, ...segments);

  const normalizedBase = path.resolve(base);
  const normalizedTarget = path.resolve(targetPath);

  if (
    normalizedTarget !== normalizedBase &&
    !normalizedTarget.startsWith(normalizedBase + path.sep)
  ) {
    return null;
  }

  return normalizedTarget;
}

/**
 * URLパスまたはファイル名として安全に扱える文字列か判定する。
 * ディレクトリ移動やパス区切り文字を含む値は拒否する。
 */
function isSafePathSegment(segment: string): boolean {
  if (!segment) return false;
  if (segment === "." || segment === "..") return false;
  if (segment.includes("/") || segment.includes("\\")) return false;
  // eslint-disable-next-line no-control-regex -- rejecting control characters is intended
  if (/[\u0000-\u001F\u007F]/u.test(segment)) return false;

  return true;
}

/**
 * ファイル取得時の Content-Disposition ヘッダーを生成する。
 * 日本語などの非ASCIIファイル名にも対応できるようfilename* にUTF-8エンコード済みの値を設定する。
 */
function createContentDisposition(filename: string) {
  const encodedFilename = encodeURIComponent(filename);

  return `inline; filename="${encodedFilename}"; filename*=UTF-8''${encodedFilename}`;
}

/**
 * 指定されたフォルダ内のファイル一覧をJSONで返却する。
 * サブフォルダは一覧に含めず、ファイルのみを返却する。
 */
async function getFolderFiles(folder: string[], targetDir: string) {
  const entries = await readdir(targetDir, { withFileTypes: true });

  const files = await Promise.all(
    entries
      .filter((entry) => entry.isFile())
      .map(async (entry) => {
        const filename = entry.name;
        const filePath = path.join(targetDir, filename);
        const fileStat = await stat(filePath);

        return {
          filename,
          size: fileStat.size,
          createdAt: fileStat.birthtime.toISOString(),
          updatedAt: fileStat.mtime.toISOString(),
          url: `/api/files/${[...folder, filename]
            .map(encodeURIComponent)
            .join("/")}`,
        };
      })
  );

  const response: GetFolderFilesResponse = {
    path: folder.join("/"),
    files,
  };

  return NextResponse.json(response);
}

/**
 * 指定されたファイルをバイナリとして返却する。
 * 画像、PDF、Excel、テキストなど、拡張子に依存せずapplication/octet-stream として返却する。
 */
async function getFileBinary(filePath: string, filename: string) {
  const fileBuffer = await readFile(filePath);

  return new NextResponse(new Uint8Array(fileBuffer), {
    headers: {
      "Content-Type": "application/octet-stream",
      "Content-Disposition": createContentDisposition(filename),
      "Cache-Control": "no-store",
    },
  });
}

/**
 * GET API。
 *
 * 指定されたパスがフォルダの場合は、フォルダ内のファイル一覧を返却する。
 * 指定されたパスがファイルの場合は、そのファイルをバイナリとして返却する。
 *
 * 使用例:
 *
 * ```ts
 * // フォルダ内のファイル一覧を取得
 * const res = await fetch("/api/files/products");
 * const data = await res.json();
 *
 * // ファイルをバイナリで取得
 * const fileRes = await fetch("/api/files/products/sample.pdf");
 * const blob = await fileRes.blob();
 * ```
 */
export async function GET(_request: NextRequest, context: RouteParams) {
  try {
    const { folder = [] } = await context.params;

    const targetPath = safeJoin(BASE_DIR, folder);

    if (!targetPath) {
      return NextResponse.json(
        { error: "Invalid path." },
        { status: 400 }
      );
    }

    try {
      const targetStat = await stat(targetPath);

      if (targetStat.isFile()) {
        const filename = folder.at(-1);

        if (!filename) {
          return NextResponse.json(
            { error: "Invalid filename." },
            { status: 400 }
          );
        }

        return await getFileBinary(targetPath, filename);
      }

      if (targetStat.isDirectory()) {
        return await getFolderFiles(folder, targetPath);
      }

      return NextResponse.json(
        { error: "The specified path is neither a file nor a directory." },
        { status: 400 }
      );
    } catch (error: any) {
      if (error?.code === "ENOENT") {
        return NextResponse.json(
          { error: "File or directory not found." },
          { status: 404 }
        );
      }

      throw error;
    }
  } catch (error) {
    console.error(error);

    return NextResponse.json(
      { error: "Failed to process GET request." },
      { status: 500 }
    );
  }
}

/**
 * POST API。
 *
 * 指定されたフォルダに複数ファイルを保存する。
 * 同名ファイルが既に存在する場合は上書き更新する。
 *
 * 使用例:
 *
 * ```ts
 * const formData = new FormData();
 *
 * for (const file of files) {
 *   formData.append("files", file);
 * }
 *
 * const res = await fetch("/api/files/products", {
 *   method: "POST",
 *   body: formData,
 * });
 *
 * const data = await res.json();
 * ```
 */
export async function POST(request: NextRequest, context: RouteParams) {
  try {
    const { folder = [] } = await context.params;

    const targetDir = safeJoin(BASE_DIR, folder);

    if (!targetDir) {
      return NextResponse.json(
        { error: "Invalid folder path." },
        { status: 400 }
      );
    }

    const formData = await request.formData();

    let files = formData.getAll("files");

    if (files.length === 0) {
      files = formData.getAll("file");
    }

    const uploadFiles = files.filter((value): value is File => {
      return value instanceof File;
    });

    if (uploadFiles.length === 0) {
      return NextResponse.json(
        { error: "No files were provided." },
        { status: 400 }
      );
    }

    await mkdir(targetDir, { recursive: true });

    const savedFiles = [];

    for (const file of uploadFiles) {
      const filename = file.name;

      if (!isSafePathSegment(filename)) {
        return NextResponse.json(
          { error: `Invalid filename: ${filename}` },
          { status: 400 }
        );
      }

      const filePath = safeJoin(targetDir, [filename]);

      if (!filePath) {
        return NextResponse.json(
          { error: `Invalid file path: ${filename}` },
          { status: 400 }
        );
      }

      const arrayBuffer = await file.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);

      await writeFile(filePath, buffer);

      savedFiles.push({
        filename,
        size: file.size,
        url: `/api/files/${[...folder, filename]
          .map(encodeURIComponent)
          .join("/")}`,
      });
    }

    return NextResponse.json({
      message: "Files saved successfully.",
      path: folder.join("/"),
      count: savedFiles.length,
      files: savedFiles,
    });
  } catch (error) {
    console.error(error);

    return NextResponse.json(
      { error: "Failed to save files." },
      { status: 500 }
    );
  }
}

/**
 * DELETE API。
 *
 * 指定されたファイルを削除する。
 * URLは削除対象ファイルまで含める。
 * フォルダ指定のみの削除は許可しない。
 *
 * 使用例:
 *
 * ```ts
 * const res = await fetch("/api/files/products/sample.pdf", {
 *   method: "DELETE",
 * });
 *
 * const data = await res.json();
 * ```
 */
export async function DELETE(_request: NextRequest, context: RouteParams) {
  try {
    const { folder = [] } = await context.params;

    if (folder.length === 0) {
      return NextResponse.json(
        { error: "File path is required." },
        { status: 400 }
      );
    }

    const targetPath = safeJoin(BASE_DIR, folder);

    if (!targetPath) {
      return NextResponse.json(
        { error: "Invalid file path." },
        { status: 400 }
      );
    }

    const targetStat = await stat(targetPath);

    if (!targetStat.isFile()) {
      return NextResponse.json(
        { error: "The target must be a file." },
        { status: 400 }
      );
    }

    await unlink(targetPath);

    return NextResponse.json({
      message: "File deleted successfully.",
      path: folder.slice(0, -1).join("/"),
      filename: folder.at(-1),
    });
  } catch (error: any) {
    if (error?.code === "ENOENT") {
      return NextResponse.json(
        { error: "File not found." },
        { status: 404 }
      );
    }

    console.error(error);

    return NextResponse.json(
      { error: "Failed to delete file." },
      { status: 500 }
    );
  }
}
