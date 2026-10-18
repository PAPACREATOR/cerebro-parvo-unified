*** Begin Patch
*** Update File: simple_server.py
@@
-        # Orchestrate: prefer adapter direct calls when available and provide run_dir
-        orchestration = orchestrate(process, text) if 'orchestrate' in globals() else run_process_with_runner(process, text)
-
-        # If orchestration supports run_dir-aware adapters, try to call them
-        # Prefer adapter modules if implemented
-        if orchestration.get('status') in (None, 'FAIL'):
-            # Try specific adapters that write artifacts
-            try:
-                if process == 'visual_podcast':
-                    from nexus.adapters import visual_podcast as vp
-                    orchestration = vp.create_visual_podcast(text, run_dir)
-                # other run_dir-aware adapters could be invoked here
-            except Exception as e:
-                orchestration = {'status': 'FAIL', 'error': 'adapter_exception', 'message': str(e)}
+        # Orchestrate: prefer adapter direct calls when available and provide run_dir
+        orchestration = orchestrate(process, text) if 'orchestrate' in globals() else run_process_with_runner(process, text)
+
+        # If orchestration supports run_dir-aware adapters or if orchestrate returned non-OK,
+        # try to call specific run_dir-aware adapters (they use run_dir for inputs/outputs).
+        try:
+            if orchestration.get('status') != 'OK':
+                if process == 'visual_podcast':
+                    from nexus.adapters import visual_podcast as vp
+                    orchestration = vp.create_visual_podcast(text, run_dir)
+                elif process == 'convert_pdf':
+                    from nexus.adapters import convert_pdf as cp
+                    orchestration = cp.convert_pdf_from_run(run_dir)
+                elif process == 'proofread':
+                    from nexus.adapters import proofread as pr
+                    orchestration = pr.run_proofread(text, run_dir)
+        except Exception as e:
+            orchestration = {'status': 'FAIL', 'error': 'adapter_exception', 'message': str(e)}
*** End Patch
