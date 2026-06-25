# SCRIPT PARA COLETAR RSSI DO CELULAR VIA ADB
# ATENÇÃO: FUNCIONA SOMENTE NO WINDOWS, POIS USA O ADB (ANDROID DEBUG BRIDGE) PARA COMUNICAR COM O CELULAR ANDROID.

# --- CONFIGURAÇÃO ---
$global:device        = "8d:66"
$global:intervaloRssi = 0.5
$global:tempoEspera   = 60


function Write-Status {
    param([string]$texto, [string]$cor = "Gray")
    $ts  = Get-Date -Format "HH:mm:ss"
    $msg = "[$ts] $texto"
    Write-Host $msg -ForegroundColor $cor
}

# --- CONEXÃO ---
function Testar-Conexao {
    try {
        $dump = adb shell dumpsys bluetooth_manager 2>$null
        if (-not $dump) { return $false }

        $lastConn = $dump | Select-String -Pattern "Connection successful.*$global:device" -CaseSensitive:$false | Select-Object -Last 1
        $lastDisc = $dump | Select-String -Pattern "Disconnected.*$global:device"          -CaseSensitive:$false | Select-Object -Last 1

        if (-not $lastConn) { return $false }

        if (-not $lastDisc -or ($lastDisc.LineNumber -lt $lastConn.LineNumber)) {
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

function Salvar-Final {
    Write-Status "Executando cliques de salvamento final..." "Yellow"
    adb shell input tap 930 2500
    Start-Sleep -Seconds 1
    adb shell input tap 1100 2500
    Write-Status "### FIM DA EXECUCAO ###" "White"
}

# --- CAPTURA Ctrl+C / fechamento do terminal ---
$null = [Console]::TreatControlCAsInput  # não bloqueia, só garante que o finally rode
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    # Este bloco roda quando o processo PowerShell encerra (fechar janela, Stop-Process, etc.)
    adb shell input tap 930 2500
    Start-Sleep -Seconds 1
    adb shell input tap 1100 2500
} | Out-Null

# --- LOOP PRINCIPAL ---
Write-Status "### INICIANDO: MONITORANDO $global:device ###" "Green"

try {
    while ($true) {
        $estaConectado = Testar-Conexao

        if ($estaConectado) {
            Write-Status "CONECTADO. Executando cliques..." "Cyan"
            adb shell input tap 1200 500
            Start-Sleep -Milliseconds 500
            adb shell input tap 800 900
            Start-Sleep -Seconds $global:intervaloRssi
        }
        else {
            Write-Status "DESCONECTADO. Aguardando reconexao por ate $($global:tempoEspera)s (testando a cada 5s)..." "Yellow"

            $reconectou   = $false
            $inicio       = [DateTime]::Now
            $deadline     = $inicio.AddSeconds($global:tempoEspera)

            while ([DateTime]::Now -lt $deadline) {
                Start-Sleep -Seconds 5

                if (Testar-Conexao) {
                    $segundos = ([DateTime]::Now - $inicio).TotalSeconds -as [int]
                    Write-Status "RECONECTADO apos ${segundos}s! Retomando cliques..." "Green"
                    $reconectou = $true
                    break
                }
                else {
                    $restam = ($deadline - [DateTime]::Now).TotalSeconds -as [int]
                    Write-Status "  Ainda desconectado... restam ${restam}s" "DarkYellow"
                }
            }

            if (-not $reconectou) {
                Write-Status "Dispositivo nao reconectou apos $($global:tempoEspera)s. Encerrando." "Red"
                Salvar-Final
                break
            }
        }
    }
}
catch {
    Write-Status "Erro no script: $_" "Red"
    Salvar-Final
}
finally {
    Write-Status "### FIM DA EXECUCAO ###" "White"
}