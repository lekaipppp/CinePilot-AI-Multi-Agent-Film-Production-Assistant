'use client'

import * as React from 'react'
import { FileUp, Sparkles, X, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Field, FieldDescription, FieldGroup, FieldLabel } from '@/components/ui/field'
import { useProduction } from '@/components/production-provider'
import { cn } from '@/lib/utils'
import { useRouter } from 'next/navigation'

async function extractPdfText(file: File): Promise<string> {
  const pdfjs = await import('pdfjs-dist')
  pdfjs.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.mjs`

  const buffer = await file.arrayBuffer()
  const pdf = await pdfjs.getDocument({ data: buffer }).promise

  const pageTexts: string[] = []
  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber)
    const content = await page.getTextContent()
    const pageText = content.items
      .map((item) => ('str' in item ? item.str : ''))
      .join(' ')
      .trim()
    if (pageText) pageTexts.push(pageText)
  }

  return pageTexts.join('\n\n')
}

export function ScriptInput() {
  const { scriptText, setScriptText, fileName, setFileName, startAnalysis, isRunning, analyzed } =
    useProduction()
  const { analysisError } = useProduction()
  const router = useRouter()
  const [dragging, setDragging] = React.useState(false)
  const [uploadError, setUploadError] = React.useState<string | null>(null)
  const [extracting, setExtracting] = React.useState(false)
  const inputRef = React.useRef<HTMLInputElement>(null)

  const readFile = React.useCallback(
    (file: File) => {
      setUploadError(null)
      const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')

      if (isPdf) {
        setExtracting(true)
        extractPdfText(file)
          .then((text) => {
            const trimmed = text.trim()
            if (!trimmed) {
              setUploadError(
                `Couldn't find any text in "${file.name}". It may be a scanned or image-only PDF — try pasting the script text directly.`,
              )
              return
            }
            setFileName(file.name)
            setScriptText(trimmed.slice(0, 20000))
          })
          .catch((error) => {
            console.error('PDF text extraction failed:', error)
            const detail =
              error instanceof Error && error.message.length > 0 && error.message.length <= 120
                ? ` (${error.message})`
                : ''
            setUploadError(
              `Couldn't read "${file.name}" as a PDF${detail}. Try a different file.`,
            )
          })
          .finally(() => setExtracting(false))
        return
      }

      setFileName(file.name)
      const reader = new FileReader()
      reader.onload = () => setScriptText(String(reader.result ?? '').slice(0, 20000))
      reader.readAsText(file)
    },
    [setFileName, setScriptText],
  )

  const canStart = scriptText.trim().length > 0 && !isRunning

  return (
    <section
      aria-labelledby="script-input-heading"
      className="cine-glow relative overflow-hidden rounded-2xl border border-border/60 bg-card/70 shadow-lg shadow-black/20"
    >
      <div className="film-grid absolute inset-0 opacity-40" aria-hidden />

      <div className="relative flex flex-col gap-5 p-5 md:p-7">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-col gap-1.5">
            <Badge variant="outline" className="w-fit gap-1.5 border-amber/30 bg-amber/10 text-amber">
              <Sparkles className="size-3" />
              Step 1 · Director Agent
            </Badge>
            <h2 id="script-input-heading" className="text-lg font-semibold tracking-tight">
              Paste your script or upload a file
            </h2>
            <p className="max-w-xl text-pretty text-sm leading-relaxed text-muted-foreground">
              CinePilot breaks down every scene, then hands off to the location, scheduling, budget
              and risk agents automatically.
            </p>
          </div>
        </div>

        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="script-text" className="sr-only">
              Script text
            </FieldLabel>
            <div
              onDragOver={(e) => {
                e.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault()
                setDragging(false)
                const file = e.dataTransfer.files?.[0]
                if (file) readFile(file)
              }}
              className={cn(
                'relative rounded-xl border-2 border-dashed transition-colors',
                dragging ? 'border-primary bg-primary/5' : 'border-border/70 bg-background/40',
              )}
            >
              <Textarea
                id="script-text"
                value={scriptText}
                onChange={(e) => setScriptText(e.target.value)}
                placeholder={
                  'FADE IN:\n\nEXT. MOJAVE SALT FLATS - DAWN\n\nA cracked white plain stretches to the horizon…'
                }
                className="min-h-52 resize-y border-0 bg-transparent font-mono text-[13px] leading-relaxed shadow-none focus-visible:ring-0 md:min-h-64"
              />

              {dragging ? (
                <div className="pointer-events-none absolute inset-0 flex items-center justify-center rounded-xl bg-background/80">
                  <span className="flex items-center gap-2 text-sm font-medium text-primary">
                    <FileUp className="size-4" />
                    Drop your script to import
                  </span>
                </div>
              ) : null}
            </div>
            <FieldDescription>
              Supports .txt, .fountain, and .pdf screenplay files, or drag a file straight onto the
              editor.
            </FieldDescription>
          </Field>
        </FieldGroup>

        <div className="flex flex-wrap items-center gap-2">
          <input
            ref={inputRef}
            type="file"
            accept=".txt,.fountain,.md,.pdf,text/plain,application/pdf"
            className="sr-only"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) readFile(file)
              e.target.value = ''
            }}
          />
          <Button
            onClick={async () => {
              const succeeded = await startAnalysis()
              if (succeeded) router.push('/director')
            }}
            disabled={!canStart}
          >
            {isRunning ? (
              <Loader2 data-icon="inline-start" className="animate-spin" />
            ) : (
              <Sparkles data-icon="inline-start" />
            )}
            {isRunning ? 'Running agents…' : analyzed ? 'Re-run analysis' : 'Start Analysis'}
          </Button>
          <Button
            variant="outline"
            onClick={() => inputRef.current?.click()}
            disabled={extracting}
          >
            {extracting ? (
              <Loader2 data-icon="inline-start" className="animate-spin" />
            ) : (
              <FileUp data-icon="inline-start" />
            )}
            {extracting ? 'Reading PDF…' : 'Upload file'}
          </Button>

          {fileName ? (
            <Badge variant="secondary" className="gap-1.5">
              {fileName}
              <button
                type="button"
                onClick={() => {
                  setFileName(null)
                  setScriptText('')
                }}
                className="rounded-full opacity-70 hover:opacity-100"
              >
                <X className="size-3" />
                <span className="sr-only">Remove file</span>
              </button>
            </Badge>
          ) : null}

          <span className="ml-auto font-mono text-xs text-muted-foreground">
            {scriptText.trim() ? `${scriptText.trim().split(/\s+/).length} words` : 'no input'}
          </span>
        </div>
        {uploadError ? (
          <p role="alert" className="text-sm text-destructive">
            {uploadError}
          </p>
        ) : null}
        {analysisError ? (
          <p role="alert" className="text-sm text-destructive">
            {analysisError}
          </p>
        ) : null}
      </div>
    </section>
  )
}
