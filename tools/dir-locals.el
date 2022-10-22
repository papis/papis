;;; Directory Local Variables
;;; For more information see (info "(emacs) Directory Variables")

((flycheck-mode . ((eval . (add-hook 'flycheck-mode-hook #'flycheck-pycheckers-setup))))
 (python-mode . ((eval . (let
                             ((root
                               (expand-file-name (project-root
                                                  (project-current)))))
                           (setq-local python-shell-interpreter
                                       (format "%s/env/bin/python" root)
                                       flycheck-pycheckers-args
                                       (format "--venv-path=%s/env" root)
                                       flycheck-python-flake8-executable python-shell-interpreter flycheck-python-mypy-executable python-shell-interpreter flycheck-python-pylint-executable python-shell-interpreter)))
                 (mode . flycheck)
                 (flycheck-pycheckers-checkers . (mypy3 flake8)))))
