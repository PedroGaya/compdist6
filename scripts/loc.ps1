$root = Resolve-Path "$PSScriptRoot\.."

# Non-blank, non-comment lines. Block comments are not handled, so counts are approximate.
function Loc($rel, $comment) {
  $p = Join-Path $root $rel
  if (-not (Test-Path $p)) { return 0 }
  @(Get-Content $p | Where-Object { $t = $_.Trim(); $t -ne "" -and -not $t.StartsWith($comment) }).Count
}
function LocAll($rels, $comment) { ($rels | ForEach-Object { Loc $_ $comment } | Measure-Object -Sum).Sum }

$rows = @(
  [pscustomobject]@{ Protocol="REST";    Server=Loc "node/rest/index.ts" "//"; Client=Loc "loadtest/locustfile_rest.py" "#";
                     Contract=0;                                  Generated=0 }
  [pscustomobject]@{ Protocol="SOAP";    Server=Loc "node/soap/index.ts" "//"; Client=Loc "loadtest/locustfile_soap.py" "#";
                     Contract=0;                                  Generated=Loc "schemas/streaming.wsdl" "<!--" }
  [pscustomobject]@{ Protocol="GraphQL"; Server=Loc "node/gql/index.ts"  "//"; Client=Loc "loadtest/locustfile_gql.py" "#";
                     Contract=Loc "schemas/schema.graphql" "#";   Generated=0 }
  [pscustomobject]@{ Protocol="gRPC";    Server=Loc "node/pbuf/index.ts" "//"; Client=Loc "loadtest/locustfile_pbuf.py" "#";
                     Contract=Loc "proto/streaming.proto" "//";
                     Generated=LocAll @("python/pbuf/streaming_pb2.py","python/pbuf/streaming_pb2_grpc.py") "#" }
)
foreach ($r in $rows) {
  $r | Add-Member Handwritten ($r.Server + $r.Client + $r.Contract)
  $r | Add-Member Total ($r.Handwritten + $r.Generated)
}
$shared = (Loc "node/common/repo.ts" "//") + (Loc "node/common/db.ts" "//")

$rows | Format-Table Protocol, Server, Client, Contract, Generated, Handwritten, Total -AutoSize
Write-Host "Shared by all four servers (repo.ts + db.ts, not included above): $shared LOC"

$out = Join-Path $root "results\reports"
New-Item -ItemType Directory -Force $out | Out-Null
$rows | Export-Csv (Join-Path $out "loc.csv") -NoTypeInformation
Write-Host "Wrote results\reports\loc.csv"