# pip install .
# python setup.py sdist bdist

$initFile = "py2code/__init__.py"
$versionLine = Select-String -Path $initFile -Pattern '__version__\s*=\s*["'']([\d\.]+)["'']'
if ($versionLine) {
    $version = $versionLine.Matches[0].Groups[1].Value
    Write-Host "Version: ${version}"
}

python -m build
pip install --force-reinstall "dist/py2code-${version}-py3-none-any.whl"
