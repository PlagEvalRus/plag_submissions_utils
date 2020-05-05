((python-mode . ((eval . (progn
                           (when-let* ((path (projectile-project-root))
                                       (cur-python-path (getenv "PYTHONPATH"))
                                       (missing (not (s-contains-p path cur-python-path))))
                             (setenv "PYTHONPATH" (concat path ":" cur-python-path)))
                           (pyvenv-workon "psu3"))))))
