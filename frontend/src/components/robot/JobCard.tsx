/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

"use client";
import {
  useMemo,
  useEffect,
  useLayoutEffect,
  useRef,
  useCallback,
  useState,
  useContext,
  createContext,
} from 'react'
import { useTranslations } from "next-intl"
import { Paper, Typography, Stack, FormControl, InputLabel, Select, MenuItem, Button } from '@mui/material'
import { Task } from '@mui/icons-material'
import type { SelectChangeEvent } from '@mui/material/Select'
import axios from '@/lib/axios'
import { useDialogs } from '@toolpad/core/useDialogs'
import { useNotifications } from '@toolpad/core/useNotifications'
import { JobActiveResponse } from '@/types/job'
import ActiveJobCard from '@/components/job/active/ActiveJobCard'


/** 中央寄せスクロール */
function centerElement(
  container: HTMLElement,
  el: HTMLElement,
  behavior: ScrollBehavior = 'smooth',
  deadband = 12,
) {
  const containerRect = container.getBoundingClientRect()
  const targetRect = el.getBoundingClientRect()

  const deltaTop = targetRect.top - containerRect.top
  const targetCenterOffset = deltaTop + el.offsetHeight / 2
  const desiredScrollTop = container.scrollTop + targetCenterOffset - container.clientHeight / 2

  const maxScrollTop = Math.max(0, container.scrollHeight - container.clientHeight)
  const clampedTop = Math.max(0, Math.min(desiredScrollTop, maxScrollTop))

  const containerCenterY = container.scrollTop + container.clientHeight / 2
  const targetCenterY = container.scrollTop + targetCenterOffset

  if (Math.abs(targetCenterY - containerCenterY) <= deadband) return

  container.scrollTo({ top: clampedTop, behavior })
}

function isJobForRobot(job: JobActiveResponse, robotName: string): boolean {
  const vars = Array.isArray(job.variables) ? job.variables : []
  return vars.some((v) => v?.type === "Robot" && String(v?.value) === robotName)
}

type JobsCtx = {
  jobs: JobActiveResponse[]
  fetchAll: () => Promise<void>
};

const JobActiveContext = createContext<JobsCtx | null>(null)

async function fetchActiveJobs(): Promise<JobActiveResponse[]> {
  const res = await axios.post<JobActiveResponse[]>('/domain/job.active')
  return Array.isArray(res.data) ? res.data.slice() : []
}

/** Provider */
export function JobActiveProvider({
  children,
  refreshMs = 5000,
}: {
  children: React.ReactNode
  refreshMs?: number
}) {
  const [jobs, setJobs] = useState<JobActiveResponse[]>([])

  const fetchAll = useCallback(async () => {
    try {
      const list = await fetchActiveJobs()
      setJobs(list)
    } catch {
      setJobs([])
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, refreshMs)
    return () => clearInterval(id)
  }, [fetchAll, refreshMs])

  const value = useMemo<JobsCtx>(() => ({ jobs, fetchAll }), [jobs, fetchAll])

  return (
    <JobActiveContext.Provider value={value}>
      {children}
    </JobActiveContext.Provider>
  )
}

export function SingleActiveJobCard({
  job,
  onRefresh,
  height,
  maxHeight,
}: {
  job: JobActiveResponse
  onRefresh: () => Promise<void>
  height?: number
  maxHeight?: number
}) {
  const taskContainerRef = useRef<HTMLDivElement | null>(null)
  const outerRef = useRef<HTMLDivElement | null>(null)
  const [effectiveHeight, setEffectiveHeight] = useState<number | undefined>(height)

  /**  DOMから最深のdata-current要素を探索 */
  const findTargetElement = useCallback((): HTMLElement | null => {
    const container = taskContainerRef.current
    if (!container) return null
    const el = container.querySelector('[data-current="true"]') as HTMLElement | null
    return el
  }, [])
  const prevTargetRef = useRef<HTMLElement | null>(null)

  /** センタリング実行 */
  const centerCurrent = useCallback(
    (preferSmooth = false) => {
      const container = taskContainerRef.current
      if (!container) return

      const targetEl = findTargetElement()
      if (!targetEl) return

      const targetChanged = prevTargetRef.current !== targetEl
      const behavior: ScrollBehavior =
        preferSmooth || targetChanged ? 'smooth' : 'auto'
      const deadband = behavior === 'smooth' ? 0 : 12

      centerElement(container, targetEl, behavior, deadband)
      prevTargetRef.current = targetEl
    },
    [findTargetElement],
  )

  useLayoutEffect(() => {
    if (height !== undefined) {
      setEffectiveHeight(height)
      return
    }
    if (maxHeight === undefined) {
      setEffectiveHeight(undefined)
      return
    }
    const el = outerRef.current
    if (!el) return
    const naturalHeight = el.scrollHeight
    const clamped = Math.min(naturalHeight, maxHeight)
    setEffectiveHeight(clamped)
  }, [height, maxHeight])

  useLayoutEffect(() => {
    centerCurrent(true)
  }, [centerCurrent, job.id])

  useEffect(() => {
    const container = taskContainerRef.current
    if (!container) return

    const ro = new ResizeObserver(() => centerCurrent(false))
    ro.observe(container)

    const mo = new MutationObserver(() => {
      requestAnimationFrame(() => centerCurrent(false))
    })
    mo.observe(container, {
      subtree: true,
      attributes: true,
      attributeFilter: ['data-current'],
    })

    return () => {
      ro.disconnect()
      mo.disconnect()
    }
  }, [centerCurrent, job.id])

  return (
    <div ref={outerRef}>
      <ActiveJobCard
        job={job}
        onRefresh={onRefresh}
        style={effectiveHeight !== undefined ? { height: effectiveHeight } : undefined}
        taskContainerRef={taskContainerRef}
      />
    </div>
  )
}

export default function JobCard({
  robotName,
  title,
  refreshMs = 5000,
  jobCardHeight = 500,
  enableIssueFromRobot = true,
}: {
  robotName: string
  title?: string
  refreshMs?: number
  /** ジョブカードの高さ */
  jobCardHeight?: number
  /** ロボット画面からジョブを発行するか */
  enableIssueFromRobot?: boolean
}) {
  const tJob = useTranslations("Node.job")
  const tJobActive = useTranslations("Node.job.active")
  const dialogs = useDialogs()
  const notifications = useNotifications()

  const ctx = useContext(JobActiveContext)

  const [localJobs, setLocalJobs] = useState<JobActiveResponse[] | null>(null)
  const localFetchAll = useCallback(async () => {
    try {
      const list = await fetchActiveJobs()
      setLocalJobs(list)
    } catch {
      setLocalJobs([])
    }
  }, [])

  useEffect(() => {
    if (ctx) return
    localFetchAll()
    const id = setInterval(localFetchAll, refreshMs)
    return () => clearInterval(id)
  }, [ctx, localFetchAll, refreshMs])

  const jobs = ctx ? ctx.jobs : (localJobs ?? [])
  const onRefresh = ctx ? ctx.fetchAll : localFetchAll

  const jobsForThisRobot = useMemo(
    () => jobs.filter((j) => isJobForRobot(j, robotName)),
    [jobs, robotName],
  )

  const [jobNameList, setJobNameList] = useState<string[]>([])
  const [jobNamesLoading, setJobNamesLoading] = useState<boolean>(false)
  const [jobName, setJobName] = useState<string>('')

  useEffect(() => {
    if (enableIssueFromRobot) return
    setJobNameList([])
    setJobName('')
    setJobNamesLoading(false)
  }, [enableIssueFromRobot])

  /** ジョブ名リスト取得 */
  useEffect(() => {
    if (!enableIssueFromRobot) return
    let cancelled = false
    const run = () => {
      setJobNamesLoading(true)
      fetch('/api/job-names', { cache: 'no-store' })
        .then(async (r) => {
          if (!r.ok) throw new Error(await r.text())
          return r.json()
        })
        .then((d) => {
          if (!cancelled) {
            setJobNameList(Array.isArray(d?.items) ? d.items : [])
          }
        })
        .catch(() => {
          if (!cancelled) {
            setTimeout(run, 5000)
          }
        })
        .finally(() => {
                if (!cancelled) setJobNamesLoading(false)
              })
    }
    run()
    return () => {
      cancelled = true
    }
  }, [enableIssueFromRobot])

  /** ロボット画面からジョブ実行 */
  const handleExecFromRobot = useCallback(async () => {
    if (!enableIssueFromRobot) return
    if (!jobName) return
    const ok = await dialogs.confirm(
      tJobActive('exec.content', { job: jobName }),
      {
        title: tJobActive('dialog.title'),
        okText: tJobActive('exec.ok'),
        cancelText: tJobActive('dialog.cancel'),
      },
    )
    if (!ok) return
    try {
      // 対象ジョブのワークスペース取得
      const res = await axios.post<{ [key: string]: any }>('/node/job.create', {
        func: 'fetch_workspace',
        kwargs: { name: jobName },
      })
      const workspace = res.data ?? {}
      const variables = Array.isArray(workspace.variables)
        ? workspace.variables
        : []
      const initialVars: Record<string, any> = {}
      for (const v of variables as any[]) {
        if (v?.type === 'Robot' && typeof v?.name === 'string' && v.name) {
          initialVars[v.name] = robotName
        }
      }
      await axios.post('/node/job.create', {
        func: 'active',
        kwargs: {
          name: jobName,
          ...initialVars,
        },
      })
      await onRefresh()
      notifications.show(tJobActive('exec.success', { job: jobName }), {
        severity: 'success',
        autoHideDuration: 3000,
      })
    } catch (e) {
      notifications.show(tJobActive('exec.error', { job: jobName }), {
        severity: 'error',
        autoHideDuration: 3000,
      })
    }
  }, [enableIssueFromRobot, jobName, robotName, dialogs, notifications, onRefresh, tJobActive])

  const hasActiveJob = jobsForThisRobot.length > 0

  return (
    <Paper sx={{ p: { xs: 1.5, md: 2 } }}>
      <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 700 }}>
        {title ?? tJob("name")}
      </Typography>
      {hasActiveJob ? (
        jobsForThisRobot.map((job) => (
          <SingleActiveJobCard
            key={String(job.id)}
            job={job}
            onRefresh={onRefresh}
            maxHeight={jobCardHeight}
          />
        ))
      ) : (
        <Stack spacing={1}>
          <Typography variant="body2" color="text.secondary">
            {tJob('active.none')}
          </Typography>
          {enableIssueFromRobot && (
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
              <FormControl
                fullWidth
                size="small"
                disabled={jobNamesLoading || jobNameList.length === 0}
              >
                <InputLabel id={`job-select-label-${robotName}`}>
                  {tJobActive('jobName')}
                </InputLabel>
                <Select
                  labelId={`job-select-label-${robotName}`}
                  id={`job-select-${robotName}`}
                  label={tJobActive('jobName')}
                  value={jobName}
                  onChange={(event: SelectChangeEvent) => {
                    const selected = jobNameList.find((name) => name === event.target.value)
                    setJobName(selected ?? '')
                  }}
                >
                  {jobNameList.map((name) => (
                    <MenuItem key={name} value={name}>
                      {name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="contained"
                onClick={handleExecFromRobot}
                disabled={!jobName || jobNamesLoading || jobNameList.length === 0}
                startIcon={<Task />}
                sx={{ minWidth: { xs: '100%', sm: 'fit-content' } }}
              >
                {tJobActive('name')}
              </Button>
            </Stack>
          )}
        </Stack>
      )}
    </Paper>
  )
}
