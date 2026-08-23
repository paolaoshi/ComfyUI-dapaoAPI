import { useEffect, useRef } from "react";
import type { ChapterDef } from "../registry/types";
import "./ProgressBar.css";

interface Props {
  chapters: ChapterDef[];
  cursor: { chapter: number; step: number };
  onJumpChapter(idx: number, step?: number): void;
  /**
   * Optional GitHub link rendered next to the bar; reveals/hides together
   * with the chapter list on hover. Pass `null` to hide.
   */
  githubUrl?: string | null;
}

const DEFAULT_GITHUB_URL =
  "https://github.com/ConardLi/garden-skills";

/**
 * Hidden-on-hover progress bar, fixed to the bottom of the viewport.
 * Click chapter pill or pip to jump.
 *
 * Width is content-adaptive and capped at `100vw - 32px`; if total chapters
 * (or an active chapter's step pips) overflow, the bar scrolls horizontally
 * instead of squeezing items. The active chapter is auto-scrolled into view
 * on chapter change so it's visible the moment hover reveals the bar.
 *
 * A GitHub link sits to the right of the viewport, sharing the same hover
 * trigger so it appears/disappears in sync with the bar.
 */
export function ProgressBar({
  chapters,
  cursor,
  onJumpChapter,
  githubUrl = DEFAULT_GITHUB_URL,
}: Props) {
  const activeRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    activeRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
      inline: "center",
    });
  }, [cursor.chapter]);

  return (
    <div className="pb-hover" data-no-advance>
      <div className="pb">
        {chapters.map((c, i) => {
          const isActive = i === cursor.chapter;
          return (
            <button
              key={c.id}
              ref={isActive ? activeRef : undefined}
              className={`pb-chapter ${isActive ? "pb-active" : ""}`}
              onClick={(e) => {
                e.stopPropagation();
                onJumpChapter(i, 0);
              }}
            >
              <span className="pb-num">{String(i + 1).padStart(2, "0")}</span>
              <span className="pb-title">{c.title}</span>
              {isActive && (
                <div className="pb-pips">
                  {Array.from({ length: c.narrations.length }, (_, s) => (
                    <span
                      key={s}
                      className={`pb-pip ${
                        s <= cursor.step ? "pb-pip-on" : ""
                      }`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onJumpChapter(i, s);
                      }}
                    />
                  ))}
                </div>
              )}
            </button>
          );
        })}
      </div>
      {githubUrl && (
        <a
          className="pb-github"
          href={githubUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="View source on GitHub"
          onClick={(e) => e.stopPropagation()}
        >
          <svg
            viewBox="0 0 24 24"
            width="20"
            height="20"
            aria-hidden="true"
            focusable="false"
          >
            <path
              fill="currentColor"
              d="M12 .5C5.65.5.5 5.65.5 12.02c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56 0-.27-.01-1-.02-1.96-3.2.7-3.87-1.54-3.87-1.54-.52-1.33-1.28-1.69-1.28-1.69-1.04-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.18-3.1-.12-.29-.51-1.46.11-3.04 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.79 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.58.23 2.75.12 3.04.74.81 1.18 1.84 1.18 3.1 0 4.42-2.69 5.39-5.25 5.68.41.36.78 1.06.78 2.13 0 1.54-.01 2.78-.01 3.16 0 .31.21.68.8.56 4.56-1.52 7.85-5.83 7.85-10.91C23.5 5.65 18.35.5 12 .5Z"
            />
          </svg>
        </a>
      )}
    </div>
  );
}
