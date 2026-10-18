*** Begin Patch
*** Update File: simple_server.py
@@
-        # Orchestrate: prefer adapter direct calls when available and provide run_dir
-        orchestration = orchestrate(process, text) if 'orchestrate' in globals() else run_process_with_runner(process, text)
-
-        # If orchestration supports run_dir-aware adapters or if orchestrate returned non-OK,
-        # try to call specific run_dir-aware adapters (they use run_dir for inputs/outputs).
-        try:
-            if orchestration.get('status') != 'OK':
-                if process == 'visual_podcast':
-                    from nexus.adapters import visual_podcast as vp
-                    orchestration = vp.create_visual_podcast(text, run_dir)
-                elif process == 'convert_pdf':
-                    from nexus.adapters import convert_pdf as cp
-                    orchestration = cp.convert_pdf_from_run(run_dir)
-                elif process == 'proofread':
-                    from nexus.adapters import proofread as pr
-                    orchestration = pr.run_proofread(text, run_dir)
-        except Exception as e:
-            orchestration = {'status': 'FAIL', 'error': 'adapter_exception', 'message': str(e)}
+        # Prefer running the job via the shell runner if available (scripts/runner.sh or windows/runner.ps1)
+        orchestrator_cli = None
+        runner_script = None
+        # choose platform-appropriate runner
+        if os.name == 'nt':
+            potential = os.path.join(os.path.dirname(__file__), 'windows', 'runner.ps1')
+            if os.path.exists(potential):
+                runner_script = potential
+        else:
+            potential = os.path.join(os.path.dirname(__file__), 'scripts', 'runner.sh')
+            if os.path.exists(potential):
+                runner_script = potential
+
+        if runner_script:
+            try:
+                # call the runner script which calls the Python runner (nexus.run_job)
+                import subprocess
+                cmd = [runner_script, process, text, run_dir]
+                if os.name == 'nt':
+                    # PowerShell
+                    cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', runner_script, '-process', process, '-text', text, '-run_dir', run_dir]
+                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
+                out = proc.stdout.decode('utf-8', errors='ignore')
+                try:
+                    # runner will print a JSON line produced by nexus.run_job; try to extract it
+                    import json
+                    for line in out.splitlines():
+                        try:
+                            j = json.loads(line)
+                            orchestration = j
+                            break
+                        except Exception:
+                            continue
+                except Exception:
+                    orchestration = {'status': 'FAIL', 'message': 'runner failed', 'stdout': out}
+            except Exception as e:
+                orchestration = {'status': 'FAIL', 'message': 'runner invocation exception: ' + str(e)}
+        else:
+            # Fall back to in-process orchestrator if no runner script is present
+            orchestration = orchestrate(process, text) if 'orchestrate' in globals() else run_process_with_runner(process, text)
*** End Patch
