IF OBJECT_ID('dbo.SP_libros_ultimos15_por_tipoAutor','P') IS NOT NULL
  DROP PROCEDURE dbo.SP_libros_ultimos15_por_tipoAutor;
GO
CREATE PROCEDURE dbo.SP_libros_ultimos15_por_tipoAutor
AS
BEGIN
  SET NOCOUNT ON;

  ;WITH U AS(
    SELECT p.id, p.libro_id, p.usuario_id, p.fecha_prestamo
    FROM dbo.prestamo p
    WHERE p.fecha_prestamo >= DATEADD(YEAR,-15,CAST(GETDATE() AS date))
  )
  SELECT 
      a.tipo_autor,
      c.nombre AS categoria,
      l.titulo AS libro,
      MIN(p.fecha_prestamo) AS primer_prestamo,
      COUNT(*) AS veces_prestado
  FROM U p
  JOIN dbo.libro l         ON l.id = p.libro_id
  JOIN dbo.categoria c     ON c.id = l.categoria_id
  JOIN dbo.libro_autor la  ON la.libro_id = l.id
  JOIN dbo.autor a         ON a.id = la.autor_id
  WHERE c.nombre IN (N'Terror',N'Comedia',N'Suspenso')
  GROUP BY a.tipo_autor, c.nombre, l.titulo
  ORDER BY c.nombre, a.tipo_autor, l.titulo;
END
GO
