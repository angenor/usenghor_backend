-- Migration 029 : Ajout du type CLOM à l'énumération program_type
-- IMPORTANT : ALTER TYPE ... ADD VALUE ne peut pas être dans un bloc transactionnel
ALTER TYPE program_type ADD VALUE 'clom';
