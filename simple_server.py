*** Begin Patch
*** Update File: simple_server.py
@@
-        process = choose_process(text)
-        run_id = uuid.uuid4().hex
-        result = run_process(process, text)
-        response = {
-            'run_id': run_id,
-            'process': process,
-            'status': result.get('status', 'FAIL'),
-            'envelope': result.get('envelope', {'result': None, 'trace': {'error': result}}),
-            'message': result.get('message') if result.get('message') else None,
-            'error': result.get('error') if result.get('error') else None,
-        }
+        process = choose_process(text)
+        run_id = uuid.uuid4().hex
+
+        # Create a run directory to hold inputs, outputs and metadata.
+        runs_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'runs')
+        os.makedirs(runs_root, exist_ok=True)
+        run_dir = os.path.join(runs_root, run_id)
+        os.makedirs(run_dir, exist_ok=True)
+
+        # Persist the raw request for auditing
+        try:
+            with open(os.path.join(run_dir, 'request.json'), 'w', encoding='utf-8') as rf:
+                json.dump({'text': text}, rf, ensure_ascii=False)
+        except Exception:
+            pass
+
+        # Orchestrate: prefer adapter direct calls when available and provide run_dir
+        orchestration = orchestrate(process, text) if 'orchestrate' in globals() else run_process_with_runner(process, text)
+
+        # If orchestration supports run_dir-aware adapters, try to call them
+        # Prefer adapter modules if implemented
+        if orchestration.get('status') in (None, 'FAIL'):
+            # Try specific adapters that write artifacts
+            try:
+                if process == 'visual_podcast':
+                    from nexus.adapters import visual_podcast as vp
+                    orchestration = vp.create_visual_podcast(text, run_dir)
+                # other run_dir-aware adapters could be invoked here
+            except Exception as e:
+                orchestration = {'status': 'FAIL', 'error': 'adapter_exception', 'message': str(e)}
+
+        response = {
+            'run_id': run_id,
+            'process': process,
+            'status': orchestration.get('status', 'FAIL'),
+            'envelope': orchestration.get('envelope', orchestration.get('result') or {'result': None, 'trace': {'error': orchestration.get('error')}}),
+            'message': orchestration.get('message') if orchestration.get('message') else None,
+            'error': orchestration.get('error') if orchestration.get('error') else None,
+        }
*** End Patch
