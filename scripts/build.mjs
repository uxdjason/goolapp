/**
 * build.mjs - Astro 빌드 래퍼
 * Dropbox 환경에서 발생하는 두 가지 문제를 처리합니다:
 *   1. 빌드 시작 시 dist 폴더 삭제(emptyDir) 실패 (EPERM/EBUSY)
 *   2. 빌드 후 임시폴더(dist/.prerender) 정리 실패 (EBUSY)
 *
 * 해결 방법:
 *   - 빌드 전 dist를 직접 삭제 (Dropbox 잠금 해제까지 재시도)
 *   - Astro가 새 dist를 생성할 때는 Dropbox가 아직 추적하지 않아 emptyDir 성공
 *   - 빌드 후 실패는 타임스탬프로 실제 성공 여부 판별
 */
import { spawn, execSync } from 'child_process';
import { existsSync, rmSync, statSync } from 'fs';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function removeDistWithRetry(maxMs = 10000) {
  if (!existsSync('dist')) return;
  const start = Date.now();
  while (Date.now() - start < maxMs) {
    try {
      // Dropbox가 설정한 읽기 전용 속성 제거
      try {
        execSync('attrib -r -h dist\\* /s /d', { stdio: 'ignore', shell: true });
      } catch {}
      rmSync('dist', { recursive: true, force: true });
      console.log('[build] dist 폴더 정리 완료.');
      return;
    } catch (e) {
      if (e.code === 'EBUSY' || e.code === 'EPERM') {
        const elapsed = Math.round((Date.now() - start) / 1000);
        console.log(`[build] Dropbox 잠금 해제 대기 중... (${elapsed}s)`);
        await sleep(1500);
        continue;
      }
      throw e;
    }
  }
  console.log('[build] 경고: dist 완전 삭제 실패. 빌드를 계속합니다...');
}

const buildStart = Date.now();
await removeDistWithRetry();

const proc = spawn('npx', ['astro', 'build'], {
  stdio: 'inherit',
  shell: true,
});

proc.on('close', (code) => {
  if (code === 0) {
    process.exit(0);
  }

  // 빌드 후 cleanup 실패인지 확인: 이번 빌드에서 index.html이 생성됐으면 성공
  if (existsSync('dist/index.html')) {
    const mtime = statSync('dist/index.html').mtimeMs;
    if (mtime > buildStart) {
      console.log('\n[build] ✓ 빌드 산출물 정상 생성 확인. Dropbox cleanup 경고는 무시됩니다.\n');
      process.exit(0);
    }
  }

  // 실제 빌드 실패
  process.exit(code ?? 1);
});
