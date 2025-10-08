SELECT
    sp."LongName" AS "Name",
    sp."ifc_id" AS "Guid",
    --number 
    Max(CASE WHEN p.pset_name = 'Identity Data' AND p.name = 'Number' THEN p.value END) AS Number,
    MAX(CASE WHEN p.pset_name = 'Constraints' AND p.name = 'Level' THEN p.value END) AS Level,
    MAX(CASE WHEN p.pset_name = 'Dimensions' AND p.name = 'Area' THEN TRY_CAST(p.value AS DOUBLE) END) AS Area,
    MAX(CASE WHEN p.pset_name = 'Dimensions' AND p.name = 'Volume' THEN TRY_CAST(p.value AS DOUBLE) END) AS Volume
FROM "IfcSpace" sp
         LEFT JOIN psets p
                   ON p.ifc_id = sp.ifc_id
GROUP BY sp."LongName", sp."ifc_id"
ORDER BY sp."LongName";
