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
                                       flycheck-python-flake8-executable
                                       (format "%s/env/bin/flake8" root)
                                       flycheck-python-mypy-executable
                                       (format "%s/env/bin/mypy" root)
                                       flycheck-python-pylint-executable
                                       (format "%s/env/bin/pylint" root))))
                 (mode . flycheck)
                 (flycheck-pycheckers-checkers . (mypy3 flake8)))))
